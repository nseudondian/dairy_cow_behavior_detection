import Dashboard from "@/components/pages/dashboard";
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Cow Monitoring - Dashboard",
  description: "Cow Monitoring Dashboard",
  // other metadata
};

export default function Home() {
  return (
    <>
      <Dashboard />
    </>
  );
}
