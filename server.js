const express = require('express');
const { createServer } = require('http');
const { Server } = require('socket.io');
const next = require('next');

const dev = process.env.NODE_ENV !== 'production';
const app = next({ dev });
const handle = app.getRequestHandler();

app.prepare().then(() => {
  const server = express();
  const httpServer = createServer(server);
  
  // Initialize Socket.io
  const io = new Server(httpServer, {
    cors: {
      origin: '*', // For local network testing, allow all origins
      methods: ['GET', 'POST'],
    },
  });

  io.on('connection', (socket) => {
    console.log(`[Socket] User connected: ${socket.id}`);

    // Signaling events for WebRTC
    socket.on('join-room', (roomId) => {
      socket.join(roomId);
      console.log(`[Socket] User ${socket.id} joined room ${roomId}`);
      // Notify others in the room that a new user joined
      socket.to(roomId).emit('user-connected', socket.id);
    });

    socket.on('offer', (data) => {
      socket.to(data.to).emit('offer', { from: socket.id, signal: data.signal });
    });

    socket.on('answer', (data) => {
      socket.to(data.to).emit('answer', { from: socket.id, signal: data.signal });
    });

    socket.on('ice-candidate', (data) => {
      socket.to(data.to).emit('ice-candidate', { from: socket.id, signal: data.signal });
    });

    socket.on('disconnect', () => {
      console.log(`[Socket] User disconnected: ${socket.id}`);
      // Notify rooms
      socket.broadcast.emit('user-disconnected', socket.id);
    });
  });

  // Let Next.js handle all other routes
  server.all('*', (req, res) => {
    return handle(req, res);
  });

  const PORT = process.env.PORT || 3000;
  
  httpServer.listen(PORT, '0.0.0.0', (err) => {
    if (err) throw err;
    console.log(`> Ready on http://localhost:${PORT}`);
    console.log(`> Connect via local network IP (e.g., http://192.168.x.x:${PORT})`);
  });
});
