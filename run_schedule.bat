@echo off
start /min curl --location --request GET http://192.168.0.170:8000/api/execute_scheduled_tasks ^
--header 'Content-Type:application/json' ^
--data "{ \"device_id\": 0}"