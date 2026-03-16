"use client";

import { useEffect, useState } from "react";

interface CoxinhaItem {
  id: number;
  x: number;
  size: number;
  duration: number;
  delay: number;
  opacity: number;
  rotStart: number;
  rotEnd: number;
}

function generateCoxinhas(count: number): CoxinhaItem[] {
  return Array.from({ length: count }, (_, i) => ({
    id: i,
    x: Math.random() * 100,
    size: 28 + Math.random() * 36,
    duration: 7 + Math.random() * 10,
    delay: Math.random() * 12,
    opacity: 0.15 + Math.random() * 0.25,
    rotStart: Math.random() * 360,
    rotEnd: Math.random() * 360 + 180,
  }));
}

export default function CoxinhaCascade({ count = 45 }: { count?: number }) {
  const [coxinhas, setCoxinhas] = useState<CoxinhaItem[]>([]);

  useEffect(() => {
    setCoxinhas(generateCoxinhas(count));
  }, [count]);

  if (coxinhas.length === 0) return null;

  return (
    <div className="pointer-events-none fixed inset-0 overflow-hidden z-0">
      {coxinhas.map((c) => (
        <div
          key={c.id}
          className="absolute"
          style={{
            left: `${c.x}%`,
            top: 0,
            animation: `coxinha-fall ${c.duration}s linear ${c.delay}s infinite`,
            ["--coxinha-opacity" as string]: c.opacity,
            ["--rot-start" as string]: `${c.rotStart}deg`,
            ["--rot-end" as string]: `${c.rotEnd}deg`,
          }}
        >
          <svg
            width={c.size}
            height={c.size * 1.3}
            viewBox="0 0 40 52"
            fill="none"
          >
            <path
              d="M20 2C20 2 8 18 4 28C0 38 6 50 20 50C34 50 40 38 36 28C32 18 20 2 20 2Z"
              fill="#F5A623"
              fillOpacity={0.85}
            />
            <path
              d="M20 6C20 6 12 18 9 26C6 34 10 44 20 44C30 44 34 34 31 26C28 18 20 6 20 6Z"
              fill="#F5C451"
              fillOpacity={0.5}
            />
          </svg>
        </div>
      ))}
    </div>
  );
}
