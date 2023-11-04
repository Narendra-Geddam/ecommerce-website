import React, { useContext,  useState } from 'react'

// import sidebar context
import { SidebarContext } from '../Contexts/SidebarContext';
// cart context
import { CartContext } from '../Contexts/CartContext';
// import icons
import { BsBag } from 'react-icons/bs'
// import Link
import { Link } from 'react-router-dom';
// import Logo
import Logo from '../Img/logo.jpg'

function Header() {
  // header state
  const [isActive, setIsActive] = useState(false);
  const {isOpen, setIsOpen} = useContext(SidebarContext);
  const {itemAmount} = useContext(CartContext)
  // event listener
  //  useEffect(() => {
  //   window.addEventListener('scroll', () = {
  //     window.scrollY > 60 ? setIsActive(true) : setIsActive(false);
  //   });
  //  })
  return (
   <header className={`${isActive? 'bg-pink-400': 'bg-white py-2 shadow-md'} fixed w-full z-10 transition-all`} >
      <div className='container mx-auto flex items-center justify-between h-full'>
        <Link to={'/'}>
          <div>
            <img className='w-[55px] h-[50px]' src={Logo} alt="" />
          </div>
        </Link>

        {/* cart */}
        <div 
        onClick={()=> setIsOpen(!isOpen)}
        className='cursor-pointer flex relative'
        >
          <BsBag className='text-2xl'/>
          <div className='bg-red-500 absolute right-1 -bottom-2 text-[12px]w-[18px] h-[18px] text-white rounded-full flex justify-center items-center'>{itemAmount}</div>
        </div>
      </div>
      </header>
  )
}

export default Header;