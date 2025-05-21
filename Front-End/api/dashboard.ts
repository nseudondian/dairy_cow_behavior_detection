import { responseApi } from 'use-hook-api';

// export const getDashboardVideoApi = () => {
//   return responseApi(`/video_analytics`, 'get', null);
// };

export const getDashboardVideoApi = () => {
  return responseApi(`/get_all_events`, 'get', null);
};
