import uuid 
import json
from flask import Flask, request
from typing import List, Optional, Dict 
from pydantic import BaseModel 
import base64 
from openai import OpenAI
from enum import Enum 
import sys
import os
import ifcopenshell
sys.path.append(os.path.join(os.getcwd(), "secret.py"))
from secret import access_secret_version

ENUM_FILE = "keys.txt"
API_KEY = access_secret_version("OPENAI_API") 
client = OpenAI(api_key=API_KEY) 

ifc_file = "temp.ifc"
model = ifcopenshell.open(ifc_file)

with open(ENUM_FILE, "r") as file: 
    class_names = eval(file.readlines()[0])
DeviceTypeEnum = Enum("DeviceTypeEnum", {name: name for name in class_names})

#BOX SHAPE
box_dims = [1000.0,1000.0,1000.0] #in mm (x,y,z) 
 
# Create a rectangular 
box_profile = model.create_entity("IfcRectangleProfileDef", ProfileType="AREA", XDim=box_dims[0], YDim=box_dims[1]) 
 
# Position the profile at the origin in 2D space 
profile_location = model.create_entity("IfcCartesianPoint", Coordinates=[0.0, 0.0]) 
profile_placement = model.create_entity("IfcAxis2Placement2D", Location=profile_location) 
box_profile.Position = profile_placement 
 
# Extrude the profile to create a 3D box shape 
extrusion_direction = model.create_entity("IfcDirection", DirectionRatios=[0.0, 0.0, 1.0]) 
extruded_solid = model.create_entity("IfcExtrudedAreaSolid", SweptArea=box_profile, ExtrudedDirection=extrusion_direction, Depth=box_dims[2]) 
 
# Assign the extruded shape to a representation map 
axis_placement_3d = model.create_entity("IfcAxis2Placement3D", Location=model.create_entity("IfcCartesianPoint", Coordinates=[0.0, 0.0, 0.0])) 
representation_map = model.create_entity("IfcRepresentationMap", MappingOrigin=axis_placement_3d, MappedRepresentation=extruded_solid)

#BOX SHAPE


class Object(BaseModel): 
    DeviceType: DeviceTypeEnum 
    Manufacturer:str
    Model:str 
    ModelNumber: str 
    SerialNumber: str 
    Certifications: str 
    ProductionYear:str 
    AssessmentDate:str 
    NextAssessmentDate:str 
    InstallationDate:str 
    Location: str 
    AdditionalInfo: Optional[Dict[str, str]]
 
def ask_gpt(encoding): 
    response = client.beta.chat.completions.parse( 
      model="gpt-4o", 
      messages=[ 
            { 
          "role": "user", 
          "content": [ 
            { 
              "type": "text", 
              "text": f"Look at this image. Now, extract the info from the image.  Use the convential names in used in the official ifc format for any additional info found in the image.", 
            }, 
            { 
              "type": "image_url", 
              "image_url": { 
                "url":  f"data:image/png;base64,{encoding}", 
                "detail": "high" 
              }, 
            }, 
          ], 
        } 
      ], 
      temperature=0.4, 
      response_format=Object 
    ) 
     
    dic  = eval(response.choices[0].message.content)
    return dic

app = Flask(__name__)

def success_response(environ, start_response):
    status = "200 OK"
    response_header = [("content-length", "13")]
    start_response(status, response_header)
    return ["OK"]

@app.post("/image")
def image():
    response = ask_gpt(request.json["encoding"])
    return response

@app.post("/add")
def add():

    base_id = request.json["id"]
    global_id = base_id + "ELEM" 
    global_id_pset = base_id + "PSET" 
    global_id_rel_properties = base_id + "PREL"

    dic = request.json
     
    key = dic["DeviceType"] 
    name = key + " " + global_id 
    location = [0.0,0.0,0.0] 
    #create object 

    Object = model.create_entity("IfcBuildingElementProxy", GlobalId=global_id, Name=name) 
     
    #location 
    location_point = model.create_entity("IfcCartesianPoint", Coordinates=location) 
    axis_placement = model.create_entity("IfcAxis2Placement3D", Location=location_point) 
     
    #represt it with a predefined box 
    mapped_item = model.create_entity("IfcMappedItem", MappingSource=representation_map, MappingTarget=axis_placement) 
    Object.Representation = model.create_entity("IfcProductDefinitionShape", Representations=[mapped_item]) 
     
    property_set = model.create_entity("IfcPropertySet", GlobalId=global_id_pset, Name=name) 
    property_set.HasProperties = [] 
     
    for field in dic.keys(): 
      new_property = model.create_entity("IfcPropertySingleValue", Name=field, NominalValue=model.create_entity("IfcText", str(dic[field]))) #fix: additonal info is dict, loop throu it instead of inputing as a long a string 
      property_set.HasProperties += (new_property,) 
     
     
    model.create_entity( 
        "IfcRelDefinesByProperties", 
        GlobalId=global_id_rel_properties, 
        RelatedObjects=[Object], 
        RelatingPropertyDefinition=property_set 
    ) 

    storey = model.by_type("IfcBuildingStorey")[0] 
    storey.ContainsElements[0].RelatedElements += (Object,) 
    model.write(ifc_file)
    return success_response

@app.post("/reposition")
def reposition(): 
    #global_id: str, newLocation:List[float]
    global_id = request.json["id"] + "ELEM"
    newLocation = request.json["coords"] 

    Object = model.by_id(global_id) 
    location_point = model.create_entity("IfcCartesianPoint", Coordinates=newLocation) 
    axis_placement = model.create_entity("IfcAxis2Placement3D", Location=location_point) 
    Object.ObjectPlacement = axis_placement 
    model.write(ifc_file)

    return success_response
 

@app.get("/info")
def getinfo(): 
    global_id =  request.json["id"] + "ELEM"
    Object = model.by_id(global_id) 
    pset = Object.IsDefinedBy[0].get_info()["RelatingPropertyDefinition"].HasProperties 
    dic = {} 
    for prop in pset: 
        dic[prop.Name] = prop.NominalValue.wrappedValue 
    dic["AdditionalInfo"] = eval(dic["AdditionalInfo"]) 
    return dic 
 

@app.post("/modify")
def modify(): 

    global_id =  request.json["id"] + "ELEM"
    dic =  request.json["dic"]

    Object = model.by_id(global_id) 
    pset = Object.IsDefinedBy[0].get_info()["RelatingPropertyDefinition"].HasProperties 
    for prop in pset: 
        if prop.Name in dic.keys(): 
            prop.NominalValue.wrappedValue = str(dic[prop.Name]) 
    model.write(ifc_file)
    
    return success_response


@app.post("/delete")
def delete():
    global_id = request.json["id"]
    obj_global_id = global_id + "ELEM" 
    pset_global_id = global_id + "PSET" 
    rel_global_id = global_id + "PREL" 
    Object = model.by_id(obj_global_id) 
    pset = model.by_id(pset_global_id) 
    rel = model.by_id(rel_global_id) 
    model.remove(Object) 
    model.remove(pset) 
    model.remove(rel) 
    model.write(ifc_file)
    return success_response

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
