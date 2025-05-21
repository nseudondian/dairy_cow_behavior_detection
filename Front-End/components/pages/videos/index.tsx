'use client'
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow
} from "@/components/ui/table"
import { useOpenCloseModal } from '@/jotai/modal'
import { FaUpload } from "react-icons/fa"
import { Button } from '../../ui/button'
import UploadModal, { uploadMKey } from './UploadModal'
import { useApi } from "use-hook-api"
import { useEffect } from "react"
import { getVideosApi } from "@/api/videos"
import ReactPlayer from 'react-player'
import InferenceModal, { inferenceMKey } from "./InferenceModal"


const Videos = () => {
    const openCloseModal = useOpenCloseModal()
    const [callApi, { data }] = useApi({ cache: 'video-list' })

    useEffect(() => {
        callApi(getVideosApi())
    }, [])

    useEffect(() => {
        callApi(getVideosApi(), ({ data }) => {
          console.log("📦 API video data:", data); 
        });
      }, []);
      
    const onStartInference = (item: any) => {
        openCloseModal({
            key: inferenceMKey,
            status: true,
            data: {
                video_name: item['Preview-Video']
            }

        })
    }

    return (
        <>
            <div className="text-3xl mb-4">Videos</div>
            <div className="flex gap-3 justify-end">
                <Button className='flex items-center gap-2' onClick={() => openCloseModal({
                    key: uploadMKey,
                    status: true
                })}>
                    <FaUpload />
                    Upload Video</Button>
            </div>
            <div className='bg-white dark:bg-boxdark shadow-2 rounded-lg mt-5'>

                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Video Name</TableHead>
                            <TableHead>Uploaded Date</TableHead>
                            <TableHead>Uploaded Time</TableHead>
                            <TableHead className="text-center">Preview</TableHead>
                            <TableHead className="text-center">Action</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {
                            Array.isArray(data) && data.map((item: any, index: number) => {
                                console.log('🔍 Preview Video URL:', item['Preview-Video']);
                                const isProcessed = item['Inference-Status'] === 'Processed'
                                return <TableRow key={index}>
                                    <TableCell className="font-medium">{item['Video-Name']}</TableCell>
                                    <TableCell>{item['video-Date']}</TableCell>
                                    <TableCell>{item['video-Time']}</TableCell>
                                    <TableCell className="flex justify-center">
                                        <ReactPlayer width={200} height={100} controls url={`http://127.0.0.1:5000/static/${item['Preview-Video']}`}/>
                                    </TableCell>
                                    <TableCell className="text-center">
                                        {
                                            isProcessed ?
                                                <Button variant={'outline'} className={`!bg-transparent !border !border-green-700 dark:text-white `}>
                                                    Processed
                                                </Button> :
                                                <Button variant='outline' className={`!bg-green-500 dark:text-black hover:!text-black`} onClick={() => onStartInference(item)}>
                                                    Start Inference
                                                </Button>
                                        }

                                    </TableCell>
                                </TableRow>
                            }).reverse()
                        }
                    </TableBody>
                </Table>
                <UploadModal />
                <InferenceModal />
            </div>
        </>

    )
}

export default Videos