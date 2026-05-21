import { useState, useRef, type DragEvent, type ChangeEvent } from "react";

const ACCEPT = ".pdf,.jpg,.jpeg,.png,.docx";

interface Props {
  onAnalyze: (file: File) => Promise<void>;
  loading: boolean;
  error: string | null;
}

export default function UploadZone({ onAnalyze, loading, error }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) setFile(f);
  };

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) setFile(f);
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div>
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors ${
          dragging
            ? "border-blue-400 bg-blue-400/10"
            : "border-zinc-600 bg-zinc-900 hover:border-zinc-500"
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT}
          onChange={handleChange}
          className="hidden"
        />
        {file ? (
          <div>
            <p className="text-white text-lg font-medium">{file.name}</p>
            <p className="text-zinc-400 text-sm mt-1">{formatSize(file.size)}</p>
            <button
              onClick={(e) => { e.stopPropagation(); setFile(null); }}
              className="mt-3 text-sm text-zinc-500 underline hover:text-zinc-300"
            >
              Remove
            </button>
          </div>
        ) : (
          <div>
            <svg className="mx-auto h-10 w-10 text-zinc-500 mb-3" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
            </svg>
            <p className="text-zinc-400">
              Drag &amp; drop a file here, or <span className="text-blue-400 underline">browse</span>
            </p>
            <p className="text-zinc-600 text-sm mt-1">PDF, JPG, PNG, DOCX</p>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-4 bg-red-900/40 border border-red-700 rounded-lg p-3 text-red-300 text-sm">
          {error}
        </div>
      )}

      <button
        disabled={!file || loading}
        onClick={() => file && onAnalyze(file)}
        className="mt-5 w-full py-3 rounded-lg font-semibold text-white transition-colors disabled:opacity-40 disabled:cursor-not-allowed bg-blue-600 hover:bg-blue-500 flex items-center justify-center gap-2"
      >
        {loading && (
          <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
          </svg>
        )}
        {loading ? "Analyzing..." : "Analyze Document"}
      </button>
    </div>
  );
}
