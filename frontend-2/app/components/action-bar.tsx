"use client";

import { Link2, Mic, Upload } from "lucide-react";
import { Button } from "@/app/components/ui/button";

interface ActionBarProps {
    onImportClick: () => void;
    onPasteUrlClick: () => void;
}

export function ActionBar({ onImportClick, onPasteUrlClick }: ActionBarProps) {
    return (
        <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={onPasteUrlClick}>
                <Link2 />
                Paste URL
            </Button>

            <Button variant="secondary" size="sm" onClick={onImportClick}>
                <Upload />
                Import
            </Button>

            <Button
                size="sm"
                title="Coming soon"
                disabled
                className="bg-red-600 text-white hover:bg-red-700"
            >
                <Mic />
                Record
            </Button>
        </div>
    );
}
