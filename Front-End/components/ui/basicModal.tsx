
import { ReactNode } from 'react'
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "./dialog"

interface Props {
    children: ReactNode
    open: boolean
    className?: string
    onClose?: () => void
    title?: string
    footer?: ReactNode
    disableCross?: boolean
}

const BasicModal = ({ children, title, footer, open, onClose, disableCross, className }: Props) => {
    return (
        <Dialog open={open} onOpenChange={onClose} >
            <DialogContent disableCross={disableCross} className={className}>
                <DialogHeader>
                    <DialogTitle>{title}</DialogTitle>
                </DialogHeader>
                {children}
                <DialogFooter>
                    {footer}
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}


export default BasicModal
