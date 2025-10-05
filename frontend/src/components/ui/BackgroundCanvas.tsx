import React, { useEffect, useRef, useCallback } from 'react';

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  opacity: number;
}

export const BackgroundCanvas: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();
  const particlesRef = useRef<Particle[]>([]);
  const mouseRef = useRef({ x: 0, y: 0 });
  const lastTimeRef = useRef(0);

  const createParticles = useCallback((width: number, height: number) => {
    const particles: Particle[] = [];
    const cols = 25;
    const rows = 15;
    const cellWidth = width / cols;
    const cellHeight = height / rows;

    for (let i = 0; i < cols; i++) {
      for (let j = 0; j < rows; j++) {
        const x = i * cellWidth + (Math.random() - 0.5) * cellWidth * 0.3;
        const y = j * cellHeight + (Math.random() - 0.5) * cellHeight * 0.3;
        
        // Fade out towards edges
        const centerX = width / 2;
        const centerY = height / 2;
        const distance = Math.sqrt((x - centerX) ** 2 + (y - centerY) ** 2);
        const maxDistance = Math.sqrt(centerX ** 2 + centerY ** 2);
        const fadeFactor = 1 - (distance / maxDistance) * 0.7;
        
        if (fadeFactor > 0.1) {
          particles.push({
            x,
            y,
            vx: (Math.random() - 0.5) * 0.1,
            vy: (Math.random() - 0.5) * 0.1,
            opacity: fadeFactor * 0.6
          });
        }
      }
    }
    
    return particles;
  }, []);

  const drawParticles = useCallback((ctx: CanvasRenderingContext2D, particles: Particle[], mouseX: number, mouseY: number) => {
    ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
    
    // Draw particles
    ctx.fillStyle = '#e5b94f';
    particles.forEach(particle => {
      ctx.globalAlpha = particle.opacity * 0.05;
      ctx.beginPath();
      ctx.arc(particle.x, particle.y, 1, 0, Math.PI * 2);
      ctx.fill();
    });

    // Draw connections
    ctx.strokeStyle = '#e5b94f';
    ctx.lineWidth = 0.5;
    particles.forEach((particle, i) => {
      particles.slice(i + 1).forEach(otherParticle => {
        const distance = Math.sqrt(
          (particle.x - otherParticle.x) ** 2 + 
          (particle.y - otherParticle.y) ** 2
        );
        
        if (distance < 120) {
          const opacity = (1 - distance / 120) * 0.03;
          ctx.globalAlpha = opacity;
          ctx.beginPath();
          ctx.moveTo(particle.x, particle.y);
          ctx.lineTo(otherParticle.x, otherParticle.y);
          ctx.stroke();
        }
      });
    });

    // Mouse parallax effect
    if (mouseX !== 0 && mouseY !== 0) {
      const parallaxX = (mouseX - ctx.canvas.width / 2) * 0.02;
      const parallaxY = (mouseY - ctx.canvas.height / 2) * 0.02;
      
      ctx.save();
      ctx.translate(parallaxX, parallaxY);
      ctx.globalAlpha = 0.8;
      particles.forEach(particle => {
        ctx.globalAlpha = particle.opacity * 0.05;
        ctx.beginPath();
        ctx.arc(particle.x, particle.y, 1, 0, Math.PI * 2);
        ctx.fill();
      });
      ctx.restore();
    }
  }, []);

  const animate = useCallback((currentTime: number) => {
    if (!canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const deltaTime = currentTime - lastTimeRef.current;
    lastTimeRef.current = currentTime;

    // Update particles
    particlesRef.current.forEach(particle => {
      particle.x += particle.vx * deltaTime * 0.01;
      particle.y += particle.vy * deltaTime * 0.01;
      
      // Gentle drift
      particle.x += Math.sin(currentTime * 0.0001 + particle.x * 0.01) * 0.1;
      particle.y += Math.cos(currentTime * 0.0001 + particle.y * 0.01) * 0.1;
    });

    drawParticles(ctx, particlesRef.current, mouseRef.current.x, mouseRef.current.y);
    animationRef.current = requestAnimationFrame(animate);
  }, [drawParticles]);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (canvasRef.current) {
      const rect = canvasRef.current.getBoundingClientRect();
      mouseRef.current = {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
      };
    }
  }, []);

  const handleResize = useCallback(() => {
    if (!canvasRef.current) return;
    
    const canvas = canvasRef.current;
    const container = canvas.parentElement;
    if (!container) return;

    const rect = container.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = rect.height;
    
    particlesRef.current = createParticles(canvas.width, canvas.height);
  }, [createParticles]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    handleResize();
    
    // Start animation
    animationRef.current = requestAnimationFrame(animate);
    
    // Event listeners
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('resize', handleResize);
    
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('resize', handleResize);
    };
  }, [animate, handleMouseMove, handleResize]);

  return (
    <canvas
      ref={canvasRef}
      className="particle-grid"
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        zIndex: 10
      }}
    />
  );
};
