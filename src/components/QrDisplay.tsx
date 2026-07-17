'use client';

import { QRCodeCanvas } from 'qrcode.react';
import { useEffect, useState } from 'react';

export default function QrDisplay({ roomId }: { roomId: string }) {
  const [url, setUrl] = useState('');

  useEffect(() => {
    // Dynamically get the host to construct the local URL
    if (typeof window !== 'undefined') {
      const host = window.location.host;
      const protocol = window.location.protocol;
      setUrl(`${protocol}//${host}/stream/${roomId}`);
    }
  }, [roomId]);

  if (!url) return null;

  return (
    <div className="flex flex-col items-center justify-center p-6 bg-white rounded-xl shadow-lg border border-gray-200">
      <h2 className="text-xl font-bold mb-4 text-gray-800">Scan to Connect</h2>
      <div className="bg-gray-100 p-4 rounded-lg">
        <QRCodeCanvas value={url} size={250} level="H" includeMargin />
      </div>
      <p className="mt-4 text-sm text-gray-500 text-center max-w-xs">
        Scan this QR code with another device on the same local network to join the two-way video stream.
      </p>
      <div className="mt-4 text-xs font-mono bg-gray-100 p-2 rounded break-all w-full text-center">
        {url}
      </div>
    </div>
  );
}
