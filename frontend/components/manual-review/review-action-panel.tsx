"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { submitManualReviewAction } from "@/lib/api/manual-review";

interface ReviewActionPanelProps {
  caseId: string;
  caseStatus: string;
  isAssignedToCurrentReviewer: boolean;
}

export default function ReviewActionPanel({
  caseId,
  caseStatus,
  isAssignedToCurrentReviewer,
}: ReviewActionPanelProps) {
  const router = useRouter();
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  async function runAction(action: string) {
    setError(null);

    startTransition(async () => {
      try {
        await submitManualReviewAction(caseId, {
          action,
          note: note.trim() || undefined,
        });
        if (action !== "assign") {
          setNote("");
        }
        router.refresh();
      } catch (actionError) {
        setError(
          actionError instanceof Error
            ? actionError.message
            : "Manual review action failed"
        );
      }
    });
  }

  const isResolved = caseStatus !== "open";

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="review-note">
          Reviewer Note
        </Label>
        <Textarea
          id="review-note"
          value={note}
          onChange={(event) => setNote(event.target.value)}
          placeholder="Capture your rationale, missing evidence, or final decision note"
          disabled={isPending || isResolved}
        />
      </div>

      {error ? (
        <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      ) : null}

      <div className="flex flex-wrap gap-3">
        {!isAssignedToCurrentReviewer && !isResolved ? (
          <Button
            onClick={() => runAction("assign")}
            disabled={isPending}
            className="rounded-2xl bg-slate-900 hover:bg-slate-800"
          >
            Claim Case
          </Button>
        ) : null}

        <Button
          variant="outline"
          onClick={() => runAction("note")}
          disabled={isPending || isResolved}
          className="rounded-2xl"
        >
          Save Note
        </Button>

        <Button
          onClick={() => runAction("approve")}
          disabled={isPending || isResolved}
          className="rounded-2xl bg-green-600 hover:bg-green-700"
        >
          Approve Application
        </Button>

        <Button
          variant="destructive"
          onClick={() => runAction("reject")}
          disabled={isPending || isResolved}
          className="rounded-2xl"
        >
          Reject Application
        </Button>
      </div>
    </div>
  );
}
