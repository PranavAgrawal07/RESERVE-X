import { useState, useEffect } from "react";

export interface CountdownResult {
  formatted: string;
  isExpired: boolean;
  secondsRemaining: number;
}

export function useCountdown(expiresAtIso: string): CountdownResult {
  const calculate = (): CountdownResult => {
    const target = new Date(expiresAtIso).getTime();
    const now = Date.now();
    const diff = Math.max(0, target - now);

    if (diff <= 0) {
      return {
        formatted: "00:00",
        isExpired: true,
        secondsRemaining: 0,
      };
    }

    const totalSeconds = Math.floor(diff / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;

    let formatted = "";
    if (hours > 0) {
      formatted = `${hours.toString().padStart(2, "0")}:${remainingMinutes
        .toString()
        .padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;
    } else {
      formatted = `${minutes.toString().padStart(2, "0")}:${seconds
        .toString()
        .padStart(2, "0")}`;
    }

    return {
      formatted,
      isExpired: false,
      secondsRemaining: totalSeconds,
    };
  };

  const [state, setState] = useState<CountdownResult>(calculate);

  useEffect(() => {
    const timer = setInterval(() => {
      setState(calculate());
    }, 1000);

    return () => clearInterval(timer);
  }, [expiresAtIso]);

  return state;
}
