"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { FileUp, ShieldCheck } from "lucide-react";

import { uploadDocument } from "@/lib/api/documents";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/ui/status-badge";

interface DocumentUploadCardProps {
  applicationId: string;
  documentType: string;
  title: string;
  description: string;
}

export default function DocumentUploadCard({
  applicationId,
  documentType,
  title,
  description,
}: DocumentUploadCardProps) {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [message, setMessage] = useState("");

  async function handleUpload() {
    if (!selectedFile) {
      setMessage("Please choose a file first.");
      return;
    }

    setIsUploading(true);
    setMessage("");

    try {
      await uploadDocument({
        applicationId,
        documentType,
        file: selectedFile,
      });

      setMessage("Upload successful.");
      setSelectedFile(null);

      if (inputRef.current) {
        inputRef.current.value = "";
      }

      router.refresh();
    } catch {
      setMessage("Upload failed. Please try again.");
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <div className="rounded-[28px] border border-dashed border-slate-300 bg-slate-50/80 p-5">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div className="flex gap-4">
          <div className="flex size-12 items-center justify-center rounded-2xl bg-white text-indigo-600 shadow-sm">
            <FileUp className="size-5" />
          </div>
          <div>
            <p className="font-medium text-slate-900">{title}</p>
            <p className="mt-1 text-sm leading-6 text-slate-500">{description}</p>
          </div>
        </div>
        <StatusBadge tone="cyan">required</StatusBadge>
      </div>

      <div className="mt-5 space-y-3">
        <input
          ref={inputRef}
          type="file"
          onChange={(e) => setSelectedFile(e.target.files?.[0] ?? null)}
          className="block w-full rounded-2xl border border-white bg-white px-4 py-3 text-sm text-slate-600 shadow-xs"
        />

        <Button
          type="button"
          onClick={handleUpload}
          disabled={isUploading}
          className="rounded-2xl"
        >
          {isUploading ? "Uploading..." : "Upload File"}
        </Button>

        {selectedFile ? (
          <div className="flex items-center gap-2 text-sm text-slate-600">
            <ShieldCheck className="size-4 text-emerald-600" />
            <p>Selected: {selectedFile.name}</p>
          </div>
        ) : null}

        {message ? (
          <p className="text-sm text-slate-600">{message}</p>
        ) : null}
      </div>
    </div>
  );
}
