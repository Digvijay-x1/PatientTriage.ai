import {Button} from "./ui/button";

type AttentionRowProps = {
  patientId: string;
  complaint: string;
  reason: string;
  detail: string;
  status: string;
  priority: "urgent" | "review";
  onReview?: (patientId: string) => void;
};

function AttentionRow({
  patientId,
  complaint,
  reason,
  detail,
  status,
  priority,
  onReview
}: AttentionRowProps) {
  const isUrgent = priority === "urgent";

  return (
    <div className="flex flex-col gap-4 border-b border-slate-100 p-5 last:border-b-0 sm:flex-row sm:items-center sm:justify-between">
      
      {/* Patient information */}
      <div className="flex min-w-0 items-start gap-4">
        <div
          className={`mt-1 h-10 w-1 shrink-0 rounded-full ${
            isUrgent ? "bg-red-500" : "bg-amber-400"
          }`}
        />

        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
            <span className="font-semibold text-slate-900">
              {patientId}
            </span>

            <span className="text-sm text-slate-600">
              {complaint}
            </span>
          </div>

          <p className="mt-1 text-sm text-slate-600">
            {reason}
          </p>

          <p className="mt-1 text-xs text-slate-400">
            {detail}
          </p>
        </div>
      </div>

      {/* Action */}
      <div className="flex shrink-0 items-center justify-between gap-3 sm:justify-end">
        <span
          className={`whitespace-nowrap rounded-full px-3 py-1 text-xs font-semibold ${
            isUrgent
              ? "bg-red-50 text-red-700"
              : "bg-amber-50 text-amber-700"
          }`}
        >
          {status}
        </span>

        {onReview && (
          <Button
            variant="default"
            onClick={() => onReview(patientId)}
          >
            Review
          </Button>
        )}
      </div>
    </div>
  );
}

export default AttentionRow;