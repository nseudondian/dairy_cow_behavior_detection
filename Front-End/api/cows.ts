import { responseApi } from 'use-hook-api';

export const getCowsApi = () => {
    return responseApi(`/get_cow_images`, 'get', null);
};
