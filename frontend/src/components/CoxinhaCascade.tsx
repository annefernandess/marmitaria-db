"use client";

import Image from "next/image";
import { useMemo } from "react";

interface CascadeItem {
  id: number;
  x: number;
  size: number;
  duration: number;
  delay: number;
  opacity: number;
  rotStart: number;
  rotEnd: number;
}

function generateCascadeItems(count: number, laneOffset: number): CascadeItem[] {
  const laneWidth = 100 / Math.max(count, 1);

  return Array.from({ length: count }, (_, i) => ({
    id: i,
    x:
      (((i + laneOffset) % count) * laneWidth + laneWidth * 0.15) +
      Math.random() * laneWidth * 0.7,
    size: 28 + Math.random() * 36,
    duration: 7 + Math.random() * 10,
    delay: Math.random() * 12,
    opacity: 0.15 + Math.random() * 0.25,
    rotStart: Math.random() * 360,
    rotEnd: Math.random() * 360 + 180,
  }));
}

function CoxinhaIcon({ size, opacity }: { size: number; opacity: number }) {
  return (
    <svg
      width={size}
      height={size * 1.3}
      viewBox="0 0 40 52"
      fill="none"
      aria-hidden="true"
    >
      <path
        d="M20 2C20 2 8 18 4 28C0 38 6 50 20 50C34 50 40 38 36 28C32 18 20 2 20 2Z"
        fill="#F5A623"
        fillOpacity={Math.min(opacity + 0.55, 0.9)}
      />
      <path
        d="M20 6C20 6 12 18 9 26C6 34 10 44 20 44C30 44 34 34 31 26C28 18 20 6 20 6Z"
        fill="#F5C451"
        fillOpacity={Math.min(opacity + 0.2, 0.65)}
      />
    </svg>
  );
}

function FlamengoIcon({ size, opacity }: { size: number; opacity: number }) {
  return (
    <Image
      src="/flamengo.png"
      alt=""
      aria-hidden="true"
      width={size}
      height={Math.round(size * 1.2)}
      className="select-none"
      style={{ opacity: Math.min(opacity + 0.55, 0.95) }}
      unoptimized
    />
  );
}

export default function CoxinhaCascade({ count = 45 }: { count?: number }) {
  const { coxinhas, flamengos } = useMemo(() => {
    const flamengoCount = Math.floor(count / 2);
    const coxinhaCount = count - flamengoCount;

    return {
      coxinhas: generateCascadeItems(coxinhaCount, 0),
      flamengos: generateCascadeItems(flamengoCount, 0.5),
    };
  }, [count]);

  if (coxinhas.length === 0 && flamengos.length === 0) return null;

  return (
    <div className="pointer-events-none fixed inset-0 overflow-hidden z-0">
      {coxinhas.map((c) => (
        <div
          key={`coxinha-${c.id}`}
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
          <CoxinhaIcon size={c.size} opacity={c.opacity} />
        </div>
      ))}

      {flamengos.map((f) => (
        <div
          key={`flamengo-${f.id}`}
          className="absolute"
          style={{
            left: `${f.x}%`,
            top: 0,
            animation: `coxinha-fall ${f.duration}s linear ${f.delay}s infinite`,
            ["--coxinha-opacity" as string]: f.opacity,
            ["--rot-start" as string]: `${f.rotStart}deg`,
            ["--rot-end" as string]: `${f.rotEnd}deg`,
          }}
        >
          <FlamengoIcon size={f.size} opacity={f.opacity} />
        </div>
      ))}
    </div>
  );
}
