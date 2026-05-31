import { DealDetailPage } from "@/details/DealDetailPage";

export default async function DealPage({ params }: { params: Promise<{ dealId: string }> }) {
  const { dealId } = await params;
  return <DealDetailPage dealId={dealId} />;
}
