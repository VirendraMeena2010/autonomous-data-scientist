import { ScanSearch } from "lucide-react";
import { useState } from "react";

import { AnalysisComposer } from "@/components/analyses/analysis-composer";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

interface NewAnalysisDialogProps {
  projectId: string;
}

export function NewAnalysisDialog({ projectId }: NewAnalysisDialogProps) {
  const [open, setOpen] = useState(false);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <ScanSearch aria-hidden="true" />
          New Analysis
        </Button>
      </DialogTrigger>

      <DialogContent className="max-w-2xl p-0">
        <DialogTitle className="sr-only">Create a new analysis</DialogTitle>
        <DialogDescription className="sr-only">
          Choose a dataset and submit an analytical question.
        </DialogDescription>

        <div className="p-1 sm:p-2">
          <AnalysisComposer projectId={projectId} />
        </div>
      </DialogContent>
    </Dialog>
  );
}
