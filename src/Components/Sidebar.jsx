import React,{ useContext} from 'react';

// import Link
import { Link } from 'react-router-dom';

// import icons
import { IoMdArrowForward } from 'react-icons/io';
import { FiTrash2 } from 'react-icons/fi';

// import components


// import sidebar context
import { SidebarContext } from '../Contexts/SidebarContext';
// import cart context
import { CartContext } from '../Contexts/CartContext';
import CartItem from './CartItem';

function Sidebar() {
  const { isOpen, handleClose } = useContext(SidebarContext);
  const {cart, clearCart, total, itemAmount} = useContext(CartContext);
  return (
    <div className={`${isOpen ? 'right-0' : '-right-full'} w-full bg-white fixed top-0 h-full shadow-2xl md:w-[35vw] xl:max-w-[30vw] transition-all duration-300 z-20 px-4 lg:px-[35px]`}
    >
      <div className='flex items-center justify-between py-6 border-b'>
        <div className='uppercase text-sm font-semibold'>Shopping Bag ({itemAmount})</div>

        {/* right arrow icons */}
        <div onClick={handleClose} className='cursor-pointer w-8 h-8 flex justify-center items-center'>
          <IoMdArrowForward className='text-2xl'/>
        </div>
      </div>
      <div className='flex flex-col gap-y-2 h-[435px] lg:h-[455px] overflow-y-auto overflow-x-hidden border-b'>{cart.map((item)=>{
        return <CartItem item={item} key={item.id}/>
      })}
      </div>
      <div className='flex flex-col gap-y-3 py-3 mt-2'>
        <div className='flex w-full justify-between items-center'>
          {/* total */}
          <div className='uppercase font-semibold'>
              <span className='mr-2'>Total:</span>$ {parseFloat(total).toFixed(2)}
          </div>
          {/* clear cart icon */}
          <div onClick={clearCart} className='bg-red-500 cursor-pointer py-4  text-white w-12 h-12 flex justify-center items-center text-xl'>
            <FiTrash2 />
          </div>
        </div>
        <Link to='/' className='bg-gray-200 flex p-4 justify-center items-center text-primary w-full font-medium'>View cart</Link>

        <Link to='/' className='bg-primary flex p-4 justify-center items-center text-white w-full font-medium'>Checkout</Link>
      </div>
    </div>
  )
}

export default Sidebar