// Created: 2026-01-16
// Interactive circle animation inspired by base.org/pay butterfly effect
// Updated: Full-width circle, square shapes, no glow
'use client';

import React, { useRef, useEffect, useState, useCallback } from 'react';

interface Point {
  x: number;
  y: number;
  baseX: number;
  baseY: number;
  vx: number;
  vy: number;
}

export default function InteractiveCircle() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const pointsRef = useRef<Point[]>([]);
  const mouseRef = useRef<{ x: number; y: number }>({ x: -1000, y: -1000 });
  const animationRef = useRef<number | null>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  // Configuration
  const DOT_SIZE = 3; // 3px dots
  const DOT_SPACING = 12; // 12px spacing for better performance
  const CIRCLE_RADIUS_RATIO = 0.5; // Full page width
  const MOUSE_RADIUS = 100;
  const MOUSE_STRENGTH = 25;
  const RETURN_SPEED = 0.08;
  const FRICTION = 0.9;
  // Colors: #000000/20 (Muted Blue) for idle, #000000 (Brand Blue) for active
  const DOT_COLOR_IDLE = { r: 237, g: 242, b: 253 }; // #000000/20
  const DOT_COLOR_ACTIVE = { r: 76, g: 123, b: 231 }; // #000000

  // Initialize points in a circular pattern
  const initializePoints = useCallback((width: number, height: number) => {
    const points: Point[] = [];
    const centerX = width / 2;
    const centerY = height / 2;
    // Use width as the base for radius so circle spans full page width
    const radius = width * CIRCLE_RADIUS_RATIO;

    // Create a grid, but only include points within the circle
    for (let x = DOT_SPACING; x < width; x += DOT_SPACING) {
      for (let y = DOT_SPACING; y < height; y += DOT_SPACING) {
        const dx = x - centerX;
        const dy = y - centerY;
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        // Only add points within the circle (with some fuzzy edge)
        if (distance < radius + DOT_SPACING * 2) {
          points.push({
            x,
            y,
            baseX: x,
            baseY: y,
            vx: 0,
            vy: 0,
          });
        }
      }
    }

    pointsRef.current = points;
  }, []);

  // Handle resize
  useEffect(() => {
    const handleResize = () => {
      if (canvasRef.current) {
        const rect = canvasRef.current.getBoundingClientRect();
        setDimensions({ width: rect.width, height: rect.height });
        initializePoints(rect.width, rect.height);
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [initializePoints]);

  // Handle mouse movement
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const handleMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      mouseRef.current = {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      };
    };

    const handleMouseLeave = () => {
      mouseRef.current = { x: -1000, y: -1000 };
    };

    canvas.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('mouseleave', handleMouseLeave);

    return () => {
      canvas.removeEventListener('mousemove', handleMouseMove);
      canvas.removeEventListener('mouseleave', handleMouseLeave);
    };
  }, []);

  // Animation loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    const dpr = window.devicePixelRatio || 1;
    canvas.width = dimensions.width * dpr;
    canvas.height = dimensions.height * dpr;
    ctx.scale(dpr, dpr);

    const animate = () => {
      ctx.clearRect(0, 0, dimensions.width, dimensions.height);

      const mouse = mouseRef.current;
      const points = pointsRef.current;

      points.forEach((point) => {
        // Calculate distance from mouse
        const dx = mouse.x - point.x;
        const dy = mouse.y - point.y;
        const distance = Math.sqrt(dx * dx + dy * dy);

        // Apply mouse repulsion
        if (distance < MOUSE_RADIUS && distance > 0) {
          const force = (MOUSE_RADIUS - distance) / MOUSE_RADIUS;
          const angle = Math.atan2(dy, dx);
          point.vx -= Math.cos(angle) * force * MOUSE_STRENGTH * 0.1;
          point.vy -= Math.sin(angle) * force * MOUSE_STRENGTH * 0.1;
        }

        // Apply return force (spring back to base position)
        const returnDx = point.baseX - point.x;
        const returnDy = point.baseY - point.y;
        point.vx += returnDx * RETURN_SPEED;
        point.vy += returnDy * RETURN_SPEED;

        // Apply friction
        point.vx *= FRICTION;
        point.vy *= FRICTION;

        // Update position
        point.x += point.vx;
        point.y += point.vy;

        // Calculate velocity for color transition (mouse interaction only)
        const velocity = Math.sqrt(point.vx * point.vx + point.vy * point.vy);
        const velocityFade = Math.min(1, velocity / 5);

        // Calculate size based on velocity (squares grow slightly when moving)
        const sizeFactor = 1 + velocityFade * 0.5;
        const size = DOT_SIZE * sizeFactor;

        // Interpolate color from idle (#000000/20) to active (#000000) based on velocity
        const r = Math.round(DOT_COLOR_IDLE.r + (DOT_COLOR_ACTIVE.r - DOT_COLOR_IDLE.r) * velocityFade);
        const g = Math.round(DOT_COLOR_IDLE.g + (DOT_COLOR_ACTIVE.g - DOT_COLOR_IDLE.g) * velocityFade);
        const b = Math.round(DOT_COLOR_IDLE.b + (DOT_COLOR_ACTIVE.b - DOT_COLOR_IDLE.b) * velocityFade);

        // Draw square dot (fillRect instead of arc)
        ctx.fillStyle = `rgba(${r}, ${g}, ${b}, 1.0)`;
        ctx.fillRect(point.x - size / 2, point.y - size / 2, size, size);
      });

      animationRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [dimensions]);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 w-full h-full pointer-events-auto"
      style={{
        width: '100%',
        height: '100%',
      }}
    />
  );
}
