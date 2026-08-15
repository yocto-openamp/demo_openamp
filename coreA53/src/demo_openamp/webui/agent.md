# Web UI

## Features

* Backend: instantiates a `pid_controller.ModelPidController`.
* The frontend is a NiceGUI application.
  * All fields from `pid_controller.ModelPidController` are displayed.
  * These fields can be edited.
  * The schema of `pid_controller.ModelPidController` is used to generate the UI widgets.
  * There are currently three widget types:
    * text
    * int
    * float
  * When a field is edited, the updated value is sent back to the backend over a WebSocket connection.
* Backend: when a field receives a new value, for example from the frontend, the new value is broadcast to all connected frontends.
