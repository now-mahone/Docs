// Created: 2026-01-10
'use client';

import React, { useState, useEffect } from 'react';
import { Canvas } from '@react-three/fiber';

export default function HeroBackground() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  return (
    <div className="absolute inset-0 z-0 pointer-events-none opacity-40">
      <Canvas 
        camera={{ position: [0, 0, 5], fov: 45 }}
        onError={(e) => console.error("Canvas Error:", e)}
      >
        <color attach="background" args={['#f9f9f4']} />
        <mesh>
          <sphereGeometry args={[1, 32, 32]} />
          <meshStandardMaterial color="#4c7be7" transparent opacity={0.15} />
        </mesh>
        <ambientLight intensity={0.5} />
      </Canvas>
    </div>
  );
}
