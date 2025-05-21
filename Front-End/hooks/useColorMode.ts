/* eslint-disable react-hooks/exhaustive-deps */
"use client";
import { useTheme } from "next-themes";
import useLocalStorage from "./useLocalStorage";
import { useEffect } from "react";


const useColorMode = () => {
  const [colorMode, setColorMode] = useLocalStorage("color-theme", "light");
  const { setTheme } = useTheme()

  useEffect(() => {
    setTheme(colorMode)
  }, [colorMode]);

  return [colorMode, setColorMode];
};

export default useColorMode;
