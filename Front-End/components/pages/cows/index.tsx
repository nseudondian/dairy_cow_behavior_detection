/* eslint-disable @next/next/no-img-element */
'use client'
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow
} from "@/components/ui/table"
import { Input } from "../../ui/input"
import { useApi } from "use-hook-api"
import { useEffect, useState } from "react"
import { getCowsApi } from "@/api/cows"
import { FaRegObjectGroup } from "react-icons/fa6";
import { Gallery } from "react-grid-gallery";
import ImagesModal, { imagesMKey } from "./ImagesModal"
import { useOpenCloseModal } from "@/jotai/modal"
import moment from "moment"
import { RxCross1 } from "react-icons/rx";

const CowImagesGroup = ({ images }: { images: string[] }) => {
    const [showOverlay, setShowOverlay] = useState<boolean>(false)
    const openCloseModal = useOpenCloseModal()


    return (
        <div
            className={`flex flex-wrap border border-gray-900 relative gap-2 justify-center`}
            onMouseEnter={() => setShowOverlay(true)}
            onMouseLeave={() => setShowOverlay(false)}
        >
            {
                images.slice(0, 1).map((item: string, index: number) => (
                    <img key={index} src={`${apiurl}/static/${item.replace(/^.*?Dataset/, 'Dataset')}`} alt={`Cow Image`} className="size-18 object-cover" />
                ))
            }
            {
                showOverlay &&
                <div className="absolute bg-black/70 top-0 w-full h-full justify-center items-center cursor-pointer flex" onClick={() => openCloseModal({
                    key: imagesMKey,
                    status: true,
                    data: {
                        images
                    }
                })}>
                    <FaRegObjectGroup className="text-white size-7" />
                </div>
            }
        </div>
    );
};


const apiurl = process.env.NEXT_PUBLIC_API_URL
const Cows = () => {
    const [callApi, { data }] = useApi({})
    const [filters, setFilters] = useState<any>({
        search: '',
        date: '',
        activityType: ''
    })
    const [origData, setOrigData] = useState<any>([])
    const [filterData, setFilterData] = useState<any>([])

    useEffect(() => {
        callApi(getCowsApi(), ({ data }) => {
            setOrigData(data)
            setFilterData(data)
        })
    }, [])

    useEffect(() => {
        let tempData = origData
        tempData = tempData.filter((item: any) => {
            //search on all fields
            const matchesSearch = filters.search ? Object.keys(item).some((key: any) => item[key].toString().toLowerCase().includes(filters.search.toLowerCase())) : true;
            //const matchesDate = filters.date ? item['Uploaded-Date'] === moment(filters.date).format('YYYY-MM-DD') : true;
            return matchesSearch;
        });
        setFilterData(tempData)
    }, [filters])



    return (
        <>
            <div className="flex justify-between items-center">
                <div className="text-3xl mb-4">Cows</div>
                {
                    Object.keys(filters).some((item: any) => filters[item]) &&
                    <div className='flex items-center gap-1 cursor-pointer bg-white/20 text-white/70 rounded px-3 py-1' onClick={
                        () => setFilters({
                            search: '',
                            date: '',
                            activityType: ''
                        })

                    }>
                        Clear All Filters
                        <RxCross1 />
                    </div>
                }
            </div>

            <div className='bg-white dark:bg-boxdark shadow-2 rounded-lg mt-5'>

                <Table>
                    <TableHeader>
                        <TableRow>
                            {/*    <TableHead>Cow ID</TableHead> */}
                            <TableHead>Cow ID</TableHead>
                            {/*      <TableHead>Video Name</TableHead> */}
                            <TableHead>Cow Image</TableHead>
                            {/*  <TableHead>Upload Date</TableHead>
                            <TableHead>Upload Time</TableHead> */}
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {
                            filterData?.map((item: any, index: number) => (
                                <TableRow key={index}>
                                    {/*                   <TableCell className="font-medium">{item['Cow-ID']}</TableCell> */}
                                    <TableCell className="font-medium">{item['Cluster']}</TableCell>
                                    {/*          <TableCell className="font-medium">{item['Video-Name']}</TableCell> */}
                                    <TableCell>
                                        <div className="w-[200px]">
                                            <CowImagesGroup images={item["Image-Paths"]} />
                                        </div>
                                    </TableCell>
                                    {/*  <TableCell className="font-medium">{item['Uploaded-Date']}</TableCell>
                                    <TableCell className="font-medium">{item['Uploaded-Time']}</TableCell> */}
                                </TableRow>
                            ))
                        }
                    </TableBody>
                </Table>
            </div>
            <ImagesModal />
        </>

    )
}

export default Cows