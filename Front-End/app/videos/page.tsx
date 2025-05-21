import Videos from "@/components/pages/videos";
import { Metadata } from "next";

export const metadata: Metadata = {
    title: "Cow Monitoring - Videos",
    description: "Cow Monitoring Videos",
    // other metadata
};

export default function Page() {
    return (
        <>
            <Videos />
        </>
    );
}