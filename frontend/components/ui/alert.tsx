import { cn } from "@/lib/utils";

interface AlertProps {
  children: React.ReactNode;
  className?: string;
}

interface AlertDescriptionProps {
  children: React.ReactNode;
  className?: string;
}

interface AlertTitleProps {
  children: React.ReactNode;
  className?: string;
}

export function Alert({ children, className }: AlertProps) {
  return (
    <div
      className={cn(
        "rounded-[24px] border border-amber-200 bg-amber-50/80 p-5 text-amber-950",
        className
      )}
      role="alert"
    >
      {children}
    </div>
  );
}

export function AlertTitle({ children, className }: AlertTitleProps) {
  return <h3 className={cn("font-semibold", className)}>{children}</h3>;
}

export function AlertDescription({
  children,
  className,
}: AlertDescriptionProps) {
  return <div className={cn("mt-2 text-sm leading-6", className)}>{children}</div>;
}
