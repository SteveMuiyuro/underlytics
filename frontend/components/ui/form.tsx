import * as React from "react";

import { cn } from "@/lib/utils";

function Form({
  className,
  ...props
}: React.FormHTMLAttributes<HTMLFormElement>) {
  return <form className={cn("space-y-8", className)} {...props} />;
}

function FormField({ className, ...props }: React.ComponentProps<"div">) {
  return <div className={cn("space-y-3", className)} {...props} />;
}

function FormItem({ className, ...props }: React.ComponentProps<"div">) {
  return <div className={cn("grid content-start gap-3.5", className)} {...props} />;
}

function FormLabel({ className, ...props }: React.ComponentProps<"label">) {
  return (
    <label
      className={cn("text-sm font-medium tracking-tight text-slate-800", className)}
      {...props}
    />
  );
}

function FormControl({ className, ...props }: React.ComponentProps<"div">) {
  return <div className={cn("space-y-3", className)} {...props} />;
}

function FormDescription({ className, ...props }: React.ComponentProps<"p">) {
  return (
    <p className={cn("text-sm leading-6 text-slate-500", className)} {...props} />
  );
}

function FormMessage({ className, ...props }: React.ComponentProps<"p">) {
  return (
    <p className={cn("text-sm font-medium text-red-600", className)} {...props} />
  );
}

export {
  Form,
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormDescription,
  FormMessage,
};
