import React from 'react';
import { LoginModal } from './LoginModal';
import { RegisterModal } from './RegisterModal';
import { useModal } from '@/contexts/ModalContext';

export const AuthModals: React.FC = () => {
  const {
    isLoginModalOpen,
    isRegisterModalOpen,
    openLoginModal,
    openRegisterModal,
    closeLoginModal,
    closeRegisterModal,
  } = useModal();

  return (
    <>
      <LoginModal 
        isOpen={isLoginModalOpen}
        onClose={closeLoginModal}
        onSwitchToRegister={openRegisterModal}
      />
      <RegisterModal 
        isOpen={isRegisterModalOpen}
        onClose={closeRegisterModal}
        onSwitchToLogin={openLoginModal}
      />
    </>
  );
};
