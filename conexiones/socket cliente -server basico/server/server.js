const express = require('express');
const socketIO= require('socket.io');
const http = require('http');

const path = require('path');


const app = express();
let server = http.createServer(app);

const publicPath = path.resolve(__dirname, '../public');
const port = process.env.PORT || 3000;

app.use(express.static(publicPath));

//IO = esta es la comunicacion del backendk
let io = socketIO(server);

io.on('connection', (client) => {
    
    console.log('Usuario conectado');

    client.on('disconnect', ()=> {
        console.log('Usuario desconectado');
    });

    //Escuchar al cliente
    client.on('enviarMensaje', (mensaje) => {
        console.log(mensaje);
    });

});


server.listen(port, (err) => {

    if (err) throw new Error(err);

    console.log(`Servidor corriendo en puerto ${ port }`);

});