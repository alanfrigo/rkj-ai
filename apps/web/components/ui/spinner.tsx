"use client";

import * as React from "react";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface SpinnerProps extends React.HTMLAttributes<HTMLDivElement> {
    size?: "sm" | "md" | "lg";
}

const Spinner = React.forwardRef<HTMLDivElement, SpinnerProps>(
    ({ className, size = "md", ...props }, ref) => {
        const sizeClasses = {
            sm: "h-4 w-4",
            md: "h-6 w-6",
            lg: "h-8 w-8",
        };

        return (
            <div ref={ref} className={cn("animate-spin", className)} {...props}>
                <Loader2 className={cn(sizeClasses[size], "text-muted-foreground")} />
            </div>
        );
    }
);
Spinner.displayName = "Spinner";

export { Spinner };
