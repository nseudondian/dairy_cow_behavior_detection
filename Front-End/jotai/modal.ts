//handle diff modals using key
import { atom, useAtom, useSetAtom } from "jotai";
import React, { useMemo } from "react";

export const modalKey = {
  modal: "modal",
  modal1: "modal1",
  del: "del",
  confirm: "confirm",
};

export const modalAtom = atom({});

export const useModal = () => useAtom(modalAtom);

type OpenCloseType = {
  key: string;
  status: boolean;
  data?: any;
};

export const openCloseModalAtom = atom(null, (get, set, { key, status, data }: OpenCloseType) => {
  const modal = get(modalAtom);
  if (!status) {
    set(modalAtom, {
      ...modal,
      [key]: {
        status,
        data: null,
      },
    });
  } else {
    set(modalAtom, {
      ...modal,
      [key]: {
        status,
        data,
      },
    });
  }
});

export const getModalAtom = (key: string) => atom((get: any) => get(modalAtom)[key]);

export const useModalState = (key: string) => {
  const [modalVal] = useAtom(React.useMemo(() => getModalAtom(key), []));

  return modalVal;
};

export const useOpenCloseModal = () => {
  const openCloseModal = useSetAtom(openCloseModalAtom)
  return openCloseModal

}

export const useModalAtom = (key: string) => {
  const modalVal = useModalState(key)
  const openCloseModal = useOpenCloseModal()
  return [modalVal, openCloseModal]
}
