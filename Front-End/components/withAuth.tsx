/* eslint-disable react-hooks/exhaustive-deps */
/* eslint-disable react/display-name */
'use client'
import { usePathname, useRouter } from 'next/navigation'
import { useEffect } from "react"

import userAtom from "@/jotai/authdata"
import { useAtomValue } from "jotai"

const isNotAuthRoute = (pathname: any) => {
    const authRoutes = ['/login']
    return authRoutes.includes(pathname)
}

const WithAuth = ({ children }: any) => {
    const pathname = usePathname()
    const router = useRouter()
    const user = useAtomValue(userAtom)

    useEffect(() => {
        if (!user && !isNotAuthRoute(pathname)) {
            router.push('/login')
        }
    }, [])


    return children
}

export default WithAuth
