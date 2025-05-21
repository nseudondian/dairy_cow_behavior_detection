import { useModalAtom } from '@/jotai/modal'
import { Gallery } from 'react-grid-gallery'
import BasicModal from '../../ui/basicModal'
import { Button } from '../../ui/button'
export const imagesMKey = 'imagesMKey'

const ImagesModal = () => {
    const [modalVal, openCloseModal] = useModalAtom(imagesMKey)


    console.log('modalvalll', modalVal, openCloseModal)

    const onClose = () => {
        openCloseModal({
            key: imagesMKey,
            status: false,
            data: null
        })
    }

    const apiurl = process.env.NEXT_PUBLIC_API_URL

    return (
        <BasicModal open={modalVal?.status} onClose={onClose} className='max-w-[60%]'>
            <div className='h-[70vh] overflow-auto'>
                <Gallery enableImageSelection={false} images={modalVal?.data?.images?.map((img: string) => {
                    return {
                        src: `${apiurl}/${img}`, width: 'auto',
                        height: 'auto'
                    }
                })} />
            </div>
        </BasicModal>
    )
}

export default ImagesModal