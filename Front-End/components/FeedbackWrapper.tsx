'use client'
import React, { useEffect } from 'react'
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import { useFeedbackState } from 'use-hook-api';

const FeedbackWrapper = () => {
    const { feedbackState } = useFeedbackState()
    console.log('feedback', feedbackState)
    useEffect(() => {
        if (feedbackState) {
            if (feedbackState?.type === 'success') {
                feedbackState?.message?.map((msg) => toast.success(msg))

            } else if (feedbackState.type === 'error') {
                feedbackState?.message?.map((msg) => toast.error(msg))
            }
        }
    }, [feedbackState])

    return (
        <div>
            <ToastContainer />
        </div>
    )
}

export default FeedbackWrapper