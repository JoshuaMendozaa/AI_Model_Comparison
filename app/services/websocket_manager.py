from fastapi import WebSocket
import json

class ConnectionManager:
    def __init__(self):
        #stores all currently connected websocket clients
        self.active_connections: list[WebSocket] = []   #list to hold active websocket connections
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()   #accepts the incoming websocket connection
        self.active_connections.append(websocket)    #adds the new connection to the list of active connections
        print(f"New client connected. Total clients: {len(self.active_connections)}")   #logs the new connection and the total number of active connections

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)    #removes the disconnected websocket from the list of active connections
        print(f"Client disconnected. Total clients: {len(self.active_connections)}")   #logs the disconnection and the updated total number of active connections

    async def broadcast(self, message: dict):
        #sends a message to all currently connected websocket clients. The message is expected to be a dictionary, which is then converted to a JSON string before being sent to each client.
        disconnected = []   #list to keep track of any clients that have disconnected during the broadcast
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                print(f"Error sending message to client: {e}")
                disconnected.append(connection)   #if there's an error sending the message (e.g., the client has disconnected), we catch the exception and add that connection to the list of disconnected clients
            
        for connection in disconnected:
            self.disconnect(connection)    #after attempting to send the message to all clients, we loop through any clients that were marked as disconnected and remove them from the active connections list using the disconnect method. This helps ensure that our list of active connections remains accurate and doesn't include any clients that have disconnected.


manager = ConnectionManager()   #creates a single instance of the ConnectionManager class, which can be imported and used throughout the application to manage websocket connections and broadcast messages to clients.
