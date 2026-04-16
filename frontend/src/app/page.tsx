import { TechInsightDashboard } from "../components/techinsight-dashboard";
import { getDashboardBootstrap } from "../lib/api";

export const dynamic = "force-dynamic";

export default async function Home() {
  const bootstrap = await getDashboardBootstrap();

  return <TechInsightDashboard bootstrap={bootstrap} />;
}
