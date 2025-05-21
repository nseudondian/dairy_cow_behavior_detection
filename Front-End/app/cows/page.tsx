import Cows from "@/components/pages/cows";
import { Metadata } from "next";

export const metadata: Metadata = {
    title: "Cow Monitoring - Cows",
    description: "Cow Monitoring Cows",
    // other metadata
};

export default function Page() {
    return (
        <>
            <Cows />
        </>
    );
}