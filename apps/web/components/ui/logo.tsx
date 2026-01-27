import { Mic } from "lucide-react";
import { cn } from "@/lib/utils";

interface LogoProps {
  size?: "xs" | "sm" | "md" | "lg" | "xl";
  showText?: boolean;
  className?: string;
}

const sizeMap = {
  xs: { container: "h-6 w-6", icon: "h-3 w-3", text: "text-sm" },
  sm: { container: "h-7 w-7", icon: "h-3.5 w-3.5", text: "text-base" },
  md: { container: "h-8 w-8", icon: "h-4 w-4", text: "text-lg" },
  lg: { container: "h-10 w-10", icon: "h-5 w-5", text: "text-xl" },
  xl: { container: "h-12 w-12", icon: "h-6 w-6", text: "text-2xl" },
};

export function Logo({ size = "sm", showText = true, className }: LogoProps) {
  const sizes = sizeMap[size];

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div
        className={cn(
          "rounded-md bg-primary/10 flex items-center justify-center",
          sizes.container
        )}
      >
        <Mic className={cn("text-primary", sizes.icon)} />
      </div>
      {showText && (
        <span
          className={cn(
            "font-display font-semibold tracking-tight",
            sizes.text
          )}
        >
          RKJ.AI
        </span>
      )}
    </div>
  );
}

export function LogoIcon({ size = "sm", className }: Omit<LogoProps, "showText">) {
  const sizes = sizeMap[size];

  return (
    <div
      className={cn(
        "rounded-md bg-primary/10 flex items-center justify-center",
        sizes.container,
        className
      )}
    >
      <Mic className={cn("text-primary", sizes.icon)} />
    </div>
  );
}
