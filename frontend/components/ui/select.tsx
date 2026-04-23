"use client";

import * as React from "react";
import { Select as BaseSelect } from "@base-ui/react/select";
import { Check, ChevronDown } from "lucide-react";

import { cn } from "@/lib/utils";

export interface SelectOption {
  label: string;
  value: string;
  disabled?: boolean;
}

interface SelectProps {
  value: string;
  onValueChange: (value: string) => void;
  options: SelectOption[];
  placeholder?: string;
  disabled?: boolean;
  required?: boolean;
  className?: string;
}

function Select({
  value,
  onValueChange,
  options,
  placeholder = "Select an option",
  disabled = false,
  required = false,
  className,
}: SelectProps) {
  const selectedLabel =
    options.find((option) => option.value === value)?.label ?? null;

  return (
    <BaseSelect.Root
      value={value || null}
      onValueChange={(nextValue) => onValueChange(String(nextValue ?? ""))}
      items={options}
      disabled={disabled}
      required={required}
    >
      <BaseSelect.Trigger
        className={cn(
          "flex h-11 w-full items-center justify-between rounded-2xl border border-input bg-white px-4 text-left text-sm text-slate-900 shadow-xs outline-none transition-[color,box-shadow,border-color] focus-visible:border-ring focus-visible:ring-4 focus-visible:ring-ring/15 disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
      >
        <BaseSelect.Value
          placeholder={
            <span className="text-slate-400">{placeholder}</span>
          }
        >
          {selectedLabel}
        </BaseSelect.Value>
        <BaseSelect.Icon className="text-slate-400">
          <ChevronDown className="size-4" />
        </BaseSelect.Icon>
      </BaseSelect.Trigger>

      <BaseSelect.Portal>
        <BaseSelect.Positioner
          sideOffset={8}
          className="z-50 outline-none"
        >
          <BaseSelect.Popup className="w-[var(--anchor-width)] overflow-hidden rounded-2xl border border-slate-200 bg-white p-1 shadow-[0_24px_60px_-24px_rgba(15,23,42,0.35)] outline-none">
            <BaseSelect.List className="max-h-72 overflow-y-auto">
              {options.map((option) => (
                <BaseSelect.Item
                  key={`${option.value}-${option.label}`}
                  value={option.value}
                  disabled={option.disabled}
                  className="flex cursor-default items-center justify-between rounded-xl px-3 py-2.5 text-sm text-slate-700 outline-none transition data-[highlighted]:bg-slate-100 data-[selected]:text-slate-950 data-[disabled]:pointer-events-none data-[disabled]:opacity-50"
                >
                  <BaseSelect.ItemText>{option.label}</BaseSelect.ItemText>
                  <BaseSelect.ItemIndicator className="text-indigo-600">
                    <Check className="size-4" />
                  </BaseSelect.ItemIndicator>
                </BaseSelect.Item>
              ))}
            </BaseSelect.List>
          </BaseSelect.Popup>
        </BaseSelect.Positioner>
      </BaseSelect.Portal>
    </BaseSelect.Root>
  );
}

export { Select };
