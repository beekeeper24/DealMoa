import type { VerifiedReview } from "../details/types";
import type { Submission, SubmissionListResponse, SubmissionStatus } from "../submissions/types";

export type { Submission, SubmissionListResponse, SubmissionStatus, VerifiedReview };

export type VerifiedReviewListResponse = {
  items: VerifiedReview[];
  nextCursor: string | null;
};

export type MyPageErrorResponse = {
  error: {
    code: string;
    message: string;
    details: unknown;
    traceId: string;
  };
};
