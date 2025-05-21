"use client";
import "./globals.css";
import "./data-tables-css.css";
import "./satoshi.css";
import { useState, useEffect } from "react";
import Loader from "@/components/common/Loader";

import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";
import { ThemeProvider } from "@/components/theme-provider"
import useColorMode from "@/hooks/useColorMode";
import { Axios } from 'use-hook-api'
import FeedbackWrapper from "@/components/FeedbackWrapper";
import WithAuth from "@/components/withAuth";
import { usePathname } from "next/navigation";

Axios.defaults.baseURL = process.env.NEXT_PUBLIC_API_URL


export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [colorMode, setColorMode] = useColorMode();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const pathname = usePathname();
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    setTimeout(() => setLoading(false), 1000);
  }, []);

  console.log('colorMode', colorMode)

  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <div className="dark:bg-boxdark-2 dark:text-bodydark">
          <ThemeProvider
            attribute="class"
            defaultTheme={colorMode === "dark" ? "dark" : "light"}
            enableSystem
            disableTransitionOnChange
          >
            <WithAuth >

              {loading ? (
                <Loader />
              ) : (
                pathname !== '/login' ?
                  <div className="flex h-screen overflow-hidden">
                    {/* <!-- ===== Sidebar Start ===== --> */}
                    <Sidebar
                      sidebarOpen={sidebarOpen}
                      setSidebarOpen={setSidebarOpen}
                    />
                    {/* <!-- ===== Sidebar End ===== --> */}

                    {/* <!-- ===== Content Area Start ===== --> */}
                    <div className="relative flex flex-1 flex-col overflow-y-auto overflow-x-hidden">
                      {/* <!-- ===== Header Start ===== --> */}
                      <Header
                        sidebarOpen={sidebarOpen}
                        setSidebarOpen={setSidebarOpen}
                      />
                      {/* <!-- ===== Header End ===== --> */}

                      {/* <!-- ===== Main Content Start ===== --> */}
                      <main>
                        <div className="mx-auto max-w-screen-2xl p-4 md:p-6 2xl:p-10">
                          {children}
                        </div>
                      </main>
                      {/* <!-- ===== Main Content End ===== --> */}
                    </div>
                    {/* <!-- ===== Content Area End ===== --> */}
                  </div> :
                  children
              )}
            </WithAuth>
          </ThemeProvider>
          <FeedbackWrapper />
        </div>
      </body>
    </html>
  );
}
