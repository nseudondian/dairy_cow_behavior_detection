import React from 'react'
import BasicModal from '../../ui/basicModal'
import { useModalAtom, useOpenCloseModal } from '@/jotai/modal'
import { Button } from '../../ui/button'
import { useApi, useSetFeedback } from 'use-hook-api'
import { uploadVideoApi } from '@/api/videos'
import { RxCross1 } from "react-icons/rx";
import { ReloadIcon } from "@radix-ui/react-icons"
export const uploadMKey = 'uploadMKey'


const UploadModal = () => {
    const [modalVal, openCloseModal] = useModalAtom(uploadMKey)
    const [file, setFile] = React.useState<any>(null)
    const setFeedback = useSetFeedback()
    const [callApi, { loading }] = useApi({})
    const [, { refetch }] = useApi({ cache: 'video-list' })
    const fileRef = React.useRef<any>(null)


    console.log('modalvalll', modalVal, openCloseModal)

    const onClose = () => {
        openCloseModal({
            key: uploadMKey,
            status: false,
            data: null
        })
    }

    
    // const onSubmit = () => {
    //     if (!file) {
    //         setFeedback([['Please select a file'], 'error'])
    //         return
    //     }
    
    //     const formData = new FormData()
    //     formData.append('file', file)
    
    //     callApi(uploadVideoApi(formData), (res) => {
    //         const message = (res?.message || '').toString().toLowerCase().trim()
        
    //         if (message.includes('upload') && message.includes('success')) {
    //             refetch()
    //             onClose()
    //             setFeedback([['File uploaded successfully'], 'success'])
    //         } else {
    //             setFeedback([[res?.message || 'Upload failed'], 'error'])
    //         }
    //         console.log("Upload response:", res)

    //     })
        
    // }
    const onSubmit = () => {
        if (!file) {
            setFeedback('Please select a file', 'error')
            return
        }
    
        const formData = new FormData()
        formData.append('file', file)
    
        callApi(uploadVideoApi(formData), (res) => {
            console.log("📦 Upload response:", res)
    
            const message = (res?.message || '').toString().toLowerCase().trim()
    
            if (message.includes('upload') && message.includes('success')) {
                refetch()
                onClose()
                setFeedback('File uploaded successfully', 'success')
            } else {
                setFeedback(res?.message || 'Upload failed', 'error')
            }
        })
    }
    
    

    return (
        <BasicModal open={modalVal?.status} disableCross>
            <div
                id="FileUpload"
                className="relative mb-5.5 block w-full cursor-pointer appearance-none rounded border-2 border-dashed border-green-800 bg-black/20 py-4 px-4 dark:bg-black/50 sm:py-7.5"
            >
                <input
                    ref={fileRef}
                    type="file"
                    accept="videos/*"
                    className="absolute inset-0 z-50 m-0 h-full w-full cursor-pointer p-0 opacity-0 outline-none"
                    onChange={(e) => setFile(e.target.files?.[0])}
                />
                <div className="flex flex-col items-center justify-center space-y-3">
                    <span className="flex h-10 w-10 items-center justify-center rounded-full border border-stroke bg-white dark:border-strokedark dark:bg-boxdark">
                        <svg
                            width="16"
                            height="16"
                            viewBox="0 0 16 16"
                            fill="none"
                            xmlns="http://www.w3.org/2000/svg"
                        >
                            <path
                                fillRule="evenodd"
                                clipRule="evenodd"
                                d="M1.99967 9.33337C2.36786 9.33337 2.66634 9.63185 2.66634 10V12.6667C2.66634 12.8435 2.73658 13.0131 2.8616 13.1381C2.98663 13.2631 3.1562 13.3334 3.33301 13.3334H12.6663C12.8431 13.3334 13.0127 13.2631 13.1377 13.1381C13.2628 13.0131 13.333 12.8435 13.333 12.6667V10C13.333 9.63185 13.6315 9.33337 13.9997 9.33337C14.3679 9.33337 14.6663 9.63185 14.6663 10V12.6667C14.6663 13.1971 14.4556 13.7058 14.0806 14.0809C13.7055 14.456 13.1968 14.6667 12.6663 14.6667H3.33301C2.80257 14.6667 2.29387 14.456 1.91879 14.0809C1.54372 13.7058 1.33301 13.1971 1.33301 12.6667V10C1.33301 9.63185 1.63148 9.33337 1.99967 9.33337Z"
                                fill="#3C50E0"
                            />
                            <path
                                fillRule="evenodd"
                                clipRule="evenodd"
                                d="M7.5286 1.52864C7.78894 1.26829 8.21106 1.26829 8.4714 1.52864L11.8047 4.86197C12.0651 5.12232 12.0651 5.54443 11.8047 5.80478C11.5444 6.06513 11.1223 6.06513 10.8619 5.80478L8 2.94285L5.13807 5.80478C4.87772 6.06513 4.45561 6.06513 4.19526 5.80478C3.93491 5.54443 3.93491 5.12232 4.19526 4.86197L7.5286 1.52864Z"
                                fill="#3C50E0"
                            />
                            <path
                                fillRule="evenodd"
                                clipRule="evenodd"
                                d="M7.99967 1.33337C8.36786 1.33337 8.66634 1.63185 8.66634 2.00004V10C8.66634 10.3682 8.36786 10.6667 7.99967 10.6667C7.63148 10.6667 7.33301 10.3682 7.33301 10V2.00004C7.33301 1.63185 7.63148 1.33337 7.99967 1.33337Z"
                                fill="#3C50E0"
                            />
                        </svg>
                    </span>
                    <p>
                        <span className="text-primary">Click to upload</span> or
                        drag and drop
                    </p>
                </div>
                {/* show file upload name and remove icon=react-icons */}
                {
                    file &&
                    <div className="absolute bottom-0 left-0 right-0 flex justify-between items-center p-2 z-[100]">
                        <div className="flex items-center gap-2">
                            <span className="text-white">{file?.name}</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className='bg-red-500 text-white rounded p-1' onClick={(e: any) => {
                                e.stopPropagation()
                                fileRef.current.value = ''
                                setFile(null)
                            }}>
                                <RxCross1 className="text-gray-400 size-5" />
                            </div>
                        </div>
                    </div>
                }
            </div>
            <div className="flex justify-between">
                <Button type="button" variant='secondary' className='border dark:border-white/60 dark:!text-white/60 dark:!bg-transparent' onClick={onClose}>
                    Close
                </Button>
                <Button type="button" disabled={loading} variant="default" onClick={onSubmit}>
                    {
                        loading && <ReloadIcon className="mr-2 h-4 w-4 animate-spin" />
                    }
                    Upload
                </Button>
            </div>
        </BasicModal>
    )
}

export default UploadModal