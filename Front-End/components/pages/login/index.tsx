'use client'
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import userAtom from "@/jotai/authdata";
import { useSetAtom } from "jotai";
import { Eye, EyeOff } from 'lucide-react';
import { useRouter } from "next/navigation";
import { useState } from 'react';
import { useSetFeedback } from "use-hook-api";
const Login = () => {
    const [passwordVisible, setPasswordVisible] = useState(false);
    const setUser = useSetAtom(userAtom)
    const setFeedback = useSetFeedback()
    const router = useRouter()

    const togglePasswordVisibility = () => {
        setPasswordVisible(!passwordVisible);
    };
    const onSubmit = (e: any) => {
        e.preventDefault();
        if (e.target.email.value === 'admin@admin.com' && e.target.password.value === 'admin') {
            setFeedback([['Loggedin successfully'], 'success'])
            setUser({ name: 'admin', email: 'admn@admin.com' })
            router.push('/')
        } else {
            setFeedback([['Invalid credentials'], 'error'])
        }
    };

    return (
        <>
            <div className="flex bg-black/90 min-h-[100vh] flex-1 flex-col justify-center px-6 py-12 lg:px-8">
                <div className="sm:mx-auto sm:w-full sm:max-w-sm">
                    <h2 className="mt-10 text-center text-2xl font-bold leading-9 tracking-tight text-gray-300">Sign in to your account</h2>
                </div>
                <div className="mt-10 sm:mx-auto sm:w-full sm:max-w-sm">
                    <form className="space-y-6" onSubmit={onSubmit}>
                        <div >
                            <Label className='text-white' htmlFor="email">Email</Label>
                            <Input name="email" type="email" autoComplete="email" required />
                        </div>
                        <div>
                            <Label className='text-white' htmlFor="password">Password</Label>
                            <div className="relative">
                                <Input name="password" type={passwordVisible ? 'text' : 'password'} autoComplete="password" required />
                                <button type="button" className="absolute top-1/2 transform -translate-y-1/2 right-3" onClick={togglePasswordVisibility}>
                                    {passwordVisible ? <EyeOff /> : <Eye />}
                                </button>
                            </div>
                        </div>
                        <div>
                            <Button className="w-full">Login</Button>
                        </div>
                    </form>
                </div>
            </div>
        </>
    );
}

export default Login