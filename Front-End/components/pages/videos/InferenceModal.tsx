
'use client'
import { inferenceVideoApi } from '@/api/videos'
import { useModalAtom } from '@/jotai/modal'
import { ReloadIcon } from "@radix-ui/react-icons"
import { useEffect } from 'react'
import { useApi } from 'use-hook-api'
import BasicModal from '../../ui/basicModal'

export const inferenceMKey = 'inferenceMKey'

const InferenceModal = () => {
    const [modalVal, openCloseModal] = useModalAtom(inferenceMKey)
    const [callApi, { loading }] = useApi({ successMsg: true })
    const [, { refetch }] = useApi({ cache: 'video-list' })

    useEffect(() => {
        if (modalVal?.status) {
            const formData = new FormData()
            formData.append('video_name', modalVal?.data?.video_name)

            callApi(inferenceVideoApi(formData), () => {
                refetch()
                onClose()
            })
            
        }
    }, [modalVal?.status])

    const onClose = () => {
        openCloseModal({
            key: inferenceMKey,
            status: false,
            data: null
        })
    }

    return (
        <BasicModal open={modalVal?.status}>
            <div className="flex flex-col items-center justify-center space-y-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-full border border-stroke bg-white dark:border-strokedark dark:bg-boxdark">
                    <ReloadIcon className="size-6 text-green-500 animate-spin" />
                </span>
                <div className="text-2xl font-medium text-center dark:text-white">Inference Started</div>
                <div className="text-base text-center dark:text-white/80">Please wait while we process your video</div>
                <div className="text-base text-center dark:text-white/80">This may take a while</div>
            </div>
        </BasicModal>
    )
}

export default InferenceModal




'TOSIN\'S CODE'

/* eslint-disable react-hooks/exhaustive-deps */
// import { inferenceVideoApi } from '@/api/videos'
// import { useModalAtom } from '@/jotai/modal'
// import { ReloadIcon } from "@radix-ui/react-icons"
// import { useEffect } from 'react'
// import { useApi } from 'use-hook-api'
// import BasicModal from '../../ui/basicModal'
// export const inferenceMKey = 'inferenceMKey'


// const InferenceModal = () => {
//     const [modalVal, openCloseModal] = useModalAtom(inferenceMKey)
//     const [callApi, { loading }] = useApi({ successMsg: true })
//     const [, { refetch }] = useApi({ cache: 'video-list' })

//     useEffect(() => {
//         if (modalVal?.status) {
//             const formData = new FormData()
//             formData.append('video_name', modalVal?.data?.video_name)
//             callApi(inferenceVideoApi(formData), () => {
//                 refetch()
//                 onClose()
//             })
//         }
//     }, [modalVal?.status])

//     const onClose = () => {
//         openCloseModal({
//             key: inferenceMKey,
//             status: false,
//             data: null
//         })
//     }

//     return (
//         <BasicModal open={modalVal?.status}>
//             <div className="flex flex-col items-center justify-center space-y-3">
//                 <span className="flex h-10 w-10 items-center justify-center rounded-full border border-stroke bg-white dark:border-strokedark dark:bg-boxdark">
//                     <ReloadIcon className="size-6 text-green-500 animate-spin" />
//                 </span>
//                 <div className="text-2xl font-medium text-center dark:text-white">Inference Started</div>
//                 <div className="text-base text-center dark:text-white/80">Please wait while we process your video</div>
//                 <div className="text-base text-center dark:text-white/80">This may take a while</div>
//             </div>

//         </BasicModal>
//     )
// }

// export default InferenceModal