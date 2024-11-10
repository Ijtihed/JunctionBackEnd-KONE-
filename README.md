# Main Project

This repository is part of a larger unity project. The main Unity GitHub repository that incorporates this into a mobile application one can be found here:

[Main Repository](https://github.com/FilippoGrosso02/TestBIM_proj)

# How to use

requests to `url/image`
method: POST
```json
{
	"encoding" : <base-64 encoding of image>
}
```
returns
```json
{
	...
	<ifc fields>
	...
}
```

requests to `url/add`
method: POST
```json
{
	"id" : <20 character string>
	...
	<ifc fields>
	...
}
```
returns
`200 OK`

requests to `url/reposition`
method: POST
```json
{
	"id" : <20 character string>
	"coords" : [float, float, float] <in millimeters>
}
```
returns
`200 OK`

requests to `url/info`
method: GET
```json
{
	"id" : <20 character string>
}
```
returns
```json
{
	...
	<ifc fields>
	...
}
```
requests to `url/modify`
```json
{
	"id" : <20 character string>
	...
	<ifc fields key:value that you want to change>
	...
}
```
returns
`200 OK`

requests to `url/delete`
method: POST
```json
{
	"id" : <20 character string>
}
```
returns
`200 OK`
