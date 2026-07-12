"use client";

import { useRef } from "react";
import { Upload } from "lucide-react";

interface FileUploadZoneProps {
  selectedFile: File | null;
  onChange: (file: File | null) => void;
  accept?: string;
  label?: string;
  hint?: string;
}

export function FileUploadZone({
  selectedFile,
  onChange,
  accept = "audio/*,video/*",
  label = "Drag and drop your audio or video file here, or click to browse",
  hint = "MP3, WAV, M4A, MP4 up to 500 MB",
}: FileUploadZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0] ?? null;
    onChange(file);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(e.target.files?.[0] ?? null);
  };

  return (
    <div
      onClick={() => inputRef.current?.click()}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
      className="border border-dashed border-border rounded-lg p-10 text-center cursor-pointer hover:bg-stone-50 transition-colors"
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={handleChange}
      />
      <Upload className="mx-auto h-10 w-10 text-stone-300 mb-3" />
      <p className="text-stone-500 text-sm">
        {selectedFile ? (
          <span className="font-medium text-primary">{selectedFile.name}</span>
        ) : (
          label
        )}
      </p>
      {!selectedFile && (
        <p className="text-xs text-stone-400 mt-1">{hint}</p>
      )}
    </div>
  );
}
