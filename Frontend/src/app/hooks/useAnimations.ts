import { useEffect, useState, useRef, useCallback } from "react";

/**
 * Animate a numeric value with cubic ease-out.
 * Smoothly transitions from current displayed value to the new target.
 */
export function useAnimatedValue(target: number, duration = 1200): number {
  const [display, setDisplay] = useState(0);
  const rafRef = useRef(0);
  const currentRef = useRef(0);

  useEffect(() => {
    const from = currentRef.current;
    const startTime = performance.now();

    const animate = (now: number) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const newVal = from + (target - from) * eased;
      currentRef.current = newVal;
      setDisplay(newVal);
      if (progress < 1) rafRef.current = requestAnimationFrame(animate);
    };

    rafRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(rafRef.current);
  }, [target, duration]);

  return display;
}

/**
 * 3D tilt effect for cards on mouse move.
 * Returns a ref + event handlers to attach to the card element.
 */
export function useTilt(maxTilt = 6) {
  const ref = useRef<HTMLDivElement>(null);

  const onMouseMove = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      const el = ref.current;
      if (!el) return;
      const rect = el.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width - 0.5;
      const y = (e.clientY - rect.top) / rect.height - 0.5;
      el.style.transform = `perspective(800px) rotateY(${x * maxTilt}deg) rotateX(${-y * maxTilt}deg) scale3d(1.03, 1.03, 1.03)`;
      el.style.transition = "transform 0.1s ease-out";
    },
    [maxTilt]
  );

  const onMouseLeave = useCallback(() => {
    const el = ref.current;
    if (!el) return;
    el.style.transform =
      "perspective(800px) rotateY(0deg) rotateX(0deg) scale3d(1, 1, 1)";
    el.style.transition = "transform 0.4s ease-out";
  }, []);

  return { ref, onMouseMove, onMouseLeave };
}
