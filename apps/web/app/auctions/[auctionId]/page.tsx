import { AuctionDetailPage } from "@/details/AuctionDetailPage";

export default async function AuctionPage({
  params
}: {
  params: Promise<{ auctionId: string }>;
}) {
  const { auctionId } = await params;
  return <AuctionDetailPage auctionId={auctionId} />;
}
