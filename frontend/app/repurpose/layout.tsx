import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Repurpose",
  description:
    "Turn one piece of content into platform-optimized formats — optionally translated into multiple target languages.",
};

export default function RepurposeLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return children;
}
