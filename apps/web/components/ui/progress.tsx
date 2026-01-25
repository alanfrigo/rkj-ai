"use client";

import * as React from "react";
import * as ProgressPrimitive from "@radix-ui/react-progress";
import { cn } from "@/lib/utils";

interface ProgressProps
  extends React.ComponentPropsWithoutRef<typeof ProgressPrimitive.Root> {
  showRibbon?: boolean;
  isActive?: boolean;
}

const Progress = React.forwardRef<
  React.ElementRef<typeof ProgressPrimitive.Root>,
  ProgressProps
>(({ className, value, showRibbon = false, isActive = false, ...props }, ref) => (
  <ProgressPrimitive.Root
    ref={ref}
    className={cn(
      "relative h-2 w-full overflow-hidden rounded-full bg-secondary",
      showRibbon && "h-1",
      className
    )}
    {...props}
  >
    <ProgressPrimitive.Indicator
      className={cn(
        "h-full w-full flex-1 transition-all duration-300",
        showRibbon
          ? "bg-[linear-gradient(90deg,var(--primary),var(--active))]"
          : "bg-primary",
        isActive && "shadow-[0_0_20px_rgba(139,92,246,0.4)]"
      )}
      style={{ transform: `translateX(-${100 - (value || 0)}%)` }}
    />
  </ProgressPrimitive.Root>
));
Progress.displayName = ProgressPrimitive.Root.displayName;

// Timeline Ribbon component for video player and meeting cards
interface TimelineRibbonProps extends React.HTMLAttributes<HTMLDivElement> {
  progress?: number;
  isActive?: boolean;
  markers?: { position: number; label?: string }[];
  onMarkerClick?: (position: number) => void;
  onSeek?: (position: number) => void;
}

const TimelineRibbon = React.forwardRef<HTMLDivElement, TimelineRibbonProps>(
  ({ className, progress = 0, isActive = false, markers = [], onMarkerClick, onSeek, ...props }, ref) => {
    const handleClick = (e: React.MouseEvent<HTMLDivElement>) => {
      if (!onSeek) return;
      const rect = e.currentTarget.getBoundingClientRect();
      const position = ((e.clientX - rect.left) / rect.width) * 100;
      onSeek(Math.max(0, Math.min(100, position)));
    };

    return (
      <div
        ref={ref}
        className={cn(
          "timeline-ribbon-progress relative cursor-pointer group",
          className
        )}
        onClick={handleClick}
        {...props}
      >
        <div
          className={cn(
            "timeline-ribbon-progress-bar",
            isActive && "timeline-ribbon-active"
          )}
          style={{ width: `${progress}%` }}
        />
        {markers.map((marker, index) => (
          <button
            key={index}
            className="timeline-marker"
            style={{ left: `${marker.position}%` }}
            onClick={(e) => {
              e.stopPropagation();
              onMarkerClick?.(marker.position);
            }}
            title={marker.label}
          />
        ))}
        {/* Hover preview indicator */}
        <div className="absolute inset-0 bg-primary/10 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
      </div>
    );
  }
);
TimelineRibbon.displayName = "TimelineRibbon";

// Vertical timeline ribbon for sidebar
interface TimelineRibbonVerticalProps extends React.HTMLAttributes<HTMLDivElement> {
  activeIndex?: number;
  totalItems?: number;
}

const TimelineRibbonVertical = React.forwardRef<HTMLDivElement, TimelineRibbonVerticalProps>(
  ({ className, activeIndex = -1, totalItems = 0, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "timeline-ribbon-vertical h-full relative",
          className
        )}
        {...props}
      >
        {activeIndex >= 0 && totalItems > 0 && (
          <div
            className="absolute w-full bg-primary transition-all duration-300 rounded-full"
            style={{
              height: `${100 / totalItems}%`,
              top: `${(activeIndex / totalItems) * 100}%`,
            }}
          />
        )}
      </div>
    );
  }
);
TimelineRibbonVertical.displayName = "TimelineRibbonVertical";

export { Progress, TimelineRibbon, TimelineRibbonVertical };
