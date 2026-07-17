const express = require('express');
const { createServer: createHttpServer } = require('http');
const { createServer: createHttpsServer } = require('https');
const { Server } = require('socket.io');
const next = require('next');
const fs = require('fs');
const path = require('path');

const dev = process.env.NODE_ENV !== 'production';
const app = next({ dev });
const handle = app.getRequestHandler();

// Load self-signed certificates for HTTPS (needed for camera access on LAN)
const certDir = path.join(__dirname, 'certs');
const sslOptions = {
  key: fs.readFileSync(path.join(certDir, 'key.pem')),
  cert: fs.readFileSync(path.join(certDir, 'cert.pem')),
};

app.prepare().then(() => {
  const server = express();

  // Create both HTTP and HTTPS servers
  const httpServer = createHttpServer(server);
  const httpsServer = createHttpsServer(sslOptions, server);
  
  // Initialize Socket.io on BOTH servers so it works regardless of protocol
  const ioOptions = {
    cors: {
      origin: '*',
      methods: ['GET', 'POST'],
    },
  };
  const ioHttp = new Server(httpServer, ioOptions);
  const ioHttps = new Server(httpsServer, ioOptions);

  // Shared signaling handler for both io instances
  function setupSocketHandlers(io) {
    io.on('connection', (socket) => {
      console.log(`[Socket] User connected: ${socket.id}`);

      socket.on('join-room', (roomId) => {
        if (socket.rooms.has(roomId)) return;
        socket.join(roomId);
        console.log(`[Socket] User ${socket.id} joined room ${roomId}`);
        socket.to(roomId).emit('user-connected', socket.id);
      });

      socket.on('signal', (data) => {
        console.log(`[Socket] Signal from ${socket.id} to ${data.to} (type: ${data.signal?.type || 'ice'})`);
        socket.to(data.to).emit('signal', { from: socket.id, signal: data.signal });
      });

      socket.on('disconnect', () => {
        console.log(`[Socket] User disconnected: ${socket.id}`);
        socket.broadcast.emit('user-disconnected', socket.id);
      });
    });
  }

  setupSocketHandlers(ioHttp);
  setupSocketHandlers(ioHttps);

  // Let Next.js handle all other routes
  server.use((req, res) => {
    return handle(req, res);
  });

  const HTTP_PORT = process.env.HTTP_PORT || 3001;
  const HTTPS_PORT = process.env.PORT || 3000;
  
  httpServer.listen(HTTP_PORT, '0.0.0.0', () => {
    console.log(`> HTTP  ready on http://localhost:${HTTP_PORT}`);
  });

  httpsServer.listen(HTTPS_PORT, '0.0.0.0', () => {
    console.log(`> HTTPS ready on https://localhost:${HTTPS_PORT}`);
    console.log(`>`);
    console.log(`> For camera access on other devices, use the HTTPS URL:`);
    console.log(`> https://<your-local-ip>:${HTTPS_PORT}`);
    console.log(`>`);
    console.log(`> Your browser will show a security warning — click "Advanced" then "Proceed".`);
  });
});
